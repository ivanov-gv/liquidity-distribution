package subgraph

import (
	"fmt"
	"github.com/ivanov-gv/liquidity-distribution/pkg/model"
	"github.com/shurcooL/graphql"
	"math/big"
	"strconv"
	"time"
)

type tickDto struct {
	LiquidityNet string `graphql:"liquidityNet"`
	TickIdx      string `graphql:"tickIdx"`
}

func (dto tickDto) fromDto() (model.Tick, error) {
	liquidityNet, success := new(big.Int).SetString(dto.LiquidityNet, 10)
	if !success {
		return model.Tick{}, fmt.Errorf("got error while converting liquidityNet to big.Int")
	}

	tickIdx, err := strconv.Atoi(dto.TickIdx)
	if err != nil {
		return model.Tick{}, err
	}

	return model.Tick{
		TickIdx:      tickIdx,
		LiquidityNet: liquidityNet,
	}, nil
}

type tickCurrentDto struct {
	Ticks []tickDto `graphql:"ticks(first: $first, orderBy: $order_by, orderDirection: $order_dir, where: {pool: $pool, tickIdx_lte: $tick_lte, tickIdx_gte: $tick_gte})"`
}

func (dto *tickCurrentDto) fromDto() ([]model.Tick, error) {
	ticks := make([]model.Tick, len(dto.Ticks))
	for i, _tickDto := range dto.Ticks {
		tick, err := _tickDto.fromDto()
		if err != nil {
			return nil, err
		}

		ticks[i] = tick
	}
	return ticks, nil
}

func (dto *tickCurrentDto) Next(param *map[string]any) error {
	lastTick, err := strconv.Atoi(dto.Ticks[len(dto.Ticks)-1].TickIdx)
	if err != nil {
		return err
	}

	direction := (*param)["order_dir"]
	switch direction {
	case Ascending:
		(*param)["tick_gte"] = graphql.Int(lastTick + 1)
	case Descending:
		(*param)["tick_lte"] = graphql.Int(lastTick - 1)
	}
	return nil
}

func (dto *tickCurrentDto) Enough() bool {
	if len(dto.Ticks) < limit {
		return true
	}
	return false
}

func (dto *tickCurrentDto) Append(elem ...Paginated) {
	for _, i := range elem {
		dto.Ticks = append(dto.Ticks, i.(*tickCurrentDto).Ticks...)
	}
}

func GetTicks(client Client, pool *model.Pool, lowerTick int, upperTick int, direction OrderDirection) ([]model.Tick, error) {
	var dto tickCurrentDto
	err := client.QueryPaginated(&dto, func() Paginated {
		return &tickCurrentDto{}
	},
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
	return dto.fromDto()
}

type tickDayDto struct {
	Ticks []tickDto `graphql:"tickDayDatas(first: $first, orderBy: $order_by, orderDirection: $order_dir, where: {pool: $pool, date: $date, tick_lte: $tick_lte, tick_gte: $tick_gte})"`
}

func (dto *tickDayDto) fromDto() ([]model.Tick, error) {
	ticks := make([]model.Tick, len(dto.Ticks))
	for i, _tickDto := range dto.Ticks {
		tick, err := _tickDto.fromDto()
		if err != nil {
			return nil, err
		}

		ticks[i] = tick
	}
	return ticks, nil
}

func (dto *tickDayDto) Next(param *map[string]any) error {
	lastTick, err := strconv.Atoi(dto.Ticks[len(dto.Ticks)-1].TickIdx)
	if err != nil {
		return err
	}

	direction := (*param)["order_dir"]
	switch direction {
	case Ascending:
		(*param)["tick_gte"] = graphql.Int(lastTick + 1)
	case Descending:
		(*param)["tick_lte"] = graphql.Int(lastTick - 1)
	}
	return nil
}

func (dto *tickDayDto) Enough() bool {
	if len(dto.Ticks) < limit {
		return true
	}
	return false
}

func (dto *tickDayDto) Append(elem ...Paginated) {
	for _, i := range elem {
		dto.Ticks = append(dto.Ticks, i.(*tickDayDto).Ticks...)
	}
}

func GetTicksDate(client Client, pool *model.Pool, tickLte int, tickGte int, direction OrderDirection, date time.Time) ([]model.Tick, error) {
	var dto tickDayDto
	err := client.QueryPaginated(&dto, func() Paginated {
		return &tickCurrentDto{}
	},
		map[string]any{
			"first":     graphql.Int(limit),
			"pool":      pool.Address,
			"tick_lte":  graphql.Int(tickLte),
			"tick_gte":  graphql.Int(tickGte),
			"order_by":  "tickIdx",
			"order_dir": direction,
			"date":      date.Unix() / secondsInDay,
		})
	if err != nil {
		return nil, err
	}
	return dto.fromDto()
}
