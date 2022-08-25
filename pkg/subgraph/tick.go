package subgraph

import (
	"context"
	"fmt"
	"github.com/shurcooL/graphql"
	"math/big"
	"strconv"
)

type tickDayDto struct {
	TickDayData struct {
		Date int64 `graphql:"date"`
		Tick struct {
			LiquidityNet string `graphql:"liquidityNet"`
			TickIdx      string `graphql:"tickIdx"`
		} `graphql:"tickDayDatas(first: $first, orderBy: $order_by, orderDirection: $order_dir, where: {pool: $pool, date: $date, tick_lte: $tick_lte, tick_gte: $tick_gte})"`
	}
}

func (dto *tickDayDto) fromDto() (*Tick, error) {
	liquidityNet, success := new(big.Int).SetString(dto.TickDayData.Tick.LiquidityNet, 10)
	if !success {
		return nil, fmt.Errorf("got error while converting liquidityNet to big.Int")
	}

	tick, err := strconv.Atoi(dto.TickDayData.Tick.TickIdx)
	if err != nil {
		return nil, err
	}

	return &Tick{
		TickIdx:      tick,
		LiquidityNet: liquidityNet,
	}, nil
}

type tickDto struct {
	TickData []struct {
		TickIdx      string
		LiquidityNet string
	} `graphql:"ticks(first: $first, orderBy: $order_by, orderDirection: $order_dir, where: {pool: $pool, tickIdx_lte: $tick_lte, tickIdx_gte: $tick_gte})"`
}

func (dto *tickDto) fromDto() (*[]Tick, error) {
	var tickSlice = make([]Tick, len(dto.TickData))
	for i, tick := range dto.TickData {
		liquidityNet, success := new(big.Int).SetString(tick.LiquidityNet, 10)
		if !success {
			return nil, fmt.Errorf("got error while converting liquidityNet to big.Int")
		}

		tickIdx, err := strconv.Atoi(tick.TickIdx)
		if err != nil {
			return nil, err
		}

		tickSlice[i] = Tick{
			TickIdx:      tickIdx,
			LiquidityNet: liquidityNet,
		}
	}

	return &tickSlice, nil
}

type Tick struct {
	TickIdx      int
	LiquidityNet *big.Int
}

type OrderDirection string

const (
	Ascending  OrderDirection = "asc"
	Descending OrderDirection = "desc"
)

const limit = 1000

func GetTicksForNow(client *graphql.Client, pool *Pool, tickLte int, tickGte int, direction OrderDirection) (*[]Tick, error) {
	var (
		result    tickDto
		lowerTick = tickGte
		upperTick = tickLte
	)

FetchData:
	for {
		var query tickDto
		err := client.Query(context.Background(), &query,
			map[string]any{
				"first":     graphql.Int(limit),
				"pool":      pool.Address,
				"tick_lte":  graphql.Int(upperTick),
				"tick_gte":  graphql.Int(lowerTick),
				"order_by":  "tickIdx",
				"order_dir": direction,
			})
		if err != nil {
			return nil, err
		}

		result.TickData = append(result.TickData, query.TickData...)
		if len(query.TickData) < limit {
			break FetchData
		}

		lastIndex := len(query.TickData) - 1
		lastElem, err := strconv.Atoi(query.TickData[lastIndex].TickIdx)
		if err != nil {
			return nil, err
		}

		switch direction {
		case Ascending:
			lowerTick = lastElem + 1
		case Descending:
			upperTick = lastElem - 1
		}
	}

	return result.fromDto()
}
