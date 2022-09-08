package subgraph

import (
	"context"
	"fmt"
	"math/big"
	"strconv"
	"time"
)

type tokenDto struct {
	Decimals string
	Symbol   string
}

func (dto *tokenDto) fromDto() (*Token, error) {
	var err error

	decimals, err := strconv.Atoi(dto.Decimals)
	if err != nil {
		return nil, err
	}

	return &Token{
		Decimals: decimals,
		Symbol:   dto.Symbol,
	}, nil
}

type poolDto struct {
	Pool struct {
		Id          string   `graphql:"id"`
		Tick        string   `graphql:"tick"`
		Token0      tokenDto `graphql:"token0"`
		Token1      tokenDto `graphql:"token1"`
		FeeTier     string   `graphql:"feeTier"`
		Liquidity   string   `graphql:"liquidity"`
		Token0Price string   `graphql:"token0Price"`
		Token1Price string   `graphql:"token1Price"`
	} `graphql:"pool(id: $id)"`
}

func (dto *poolDto) fromDto() (*Pool, error) {
	tick, err := strconv.Atoi(dto.Pool.Tick)
	if err != nil {
		return nil, err
	}

	token0, err := dto.Pool.Token0.fromDto()
	if err != nil {
		return nil, err
	}

	token1, err := dto.Pool.Token1.fromDto()
	if err != nil {
		return nil, err
	}

	feeTier, err := strconv.Atoi(dto.Pool.FeeTier)
	if err != nil {
		return nil, err
	}

	liquidity, success := new(big.Int).SetString(dto.Pool.Liquidity, 10)
	if !success {
		return nil, fmt.Errorf("got error while converting liquidity to big.Int")
	}

	_token0Price, err := strconv.ParseFloat(dto.Pool.Token0Price, 32)
	if err != nil {
		return nil, err
	}
	token0Price := float32(_token0Price)

	_token1Price, err := strconv.ParseFloat(dto.Pool.Token1Price, 32)
	if err != nil {
		return nil, err
	}
	token1Price := float32(_token1Price)

	return &Pool{
		Address:     dto.Pool.Id,
		Tick:        tick,
		Token0:      *token0,
		Token1:      *token1,
		FeeTier:     feeTier,
		Liquidity:   liquidity,
		Token0Price: token0Price,
		Token1Price: token1Price,
	}, nil
}

type Token struct {
	Decimals int
	Symbol   string
}

type Pool struct {
	Address     string
	Tick        int
	Token0      Token
	Token1      Token
	FeeTier     int
	Liquidity   *big.Int
	Token0Price float32
	Token1Price float32
}

func NewPool(client Client, address string) (*Pool, error) {
	var query poolDto
	err := client.Query(context.Background(), &query,
		map[string]any{
			"id": address,
		})
	if err != nil {
		return nil, err
	}
	return query.fromDto()
}

type poolDayDto struct {
	PoolDayData struct {
		Date        int64  `graphql:"date"`
		Tick        string `graphql:"tick"`
		Liquidity   string `graphql:"liquidity"`
		Token0Price string `graphql:"token0Price"`
		Token1Price string `graphql:"token1Price"`
	} `graphql:"poolDayData(id: $id)"` // id format: "pool_address-date",
	// where date is a timestamp rounded to current day by dividing by secondsInDay = 86400
}

func (dto *poolDayDto) fromDto() (*PoolDay, error) {
	date := time.Unix(dto.PoolDayData.Date, 0)

	tick, err := strconv.Atoi(dto.PoolDayData.Tick)
	if err != nil {
		return nil, err
	}

	liquidity, success := new(big.Int).SetString(dto.PoolDayData.Liquidity, 10)
	if !success {
		return nil, fmt.Errorf("got error while converting liquidity to big.Int")
	}

	_token0Price, err := strconv.ParseFloat(dto.PoolDayData.Token0Price, 32)
	if err != nil {
		return nil, err
	}
	token0Price := float32(_token0Price)

	_token1Price, err := strconv.ParseFloat(dto.PoolDayData.Token1Price, 32)
	if err != nil {
		return nil, err
	}
	token1Price := float32(_token1Price)

	return &PoolDay{
		Date:        date,
		Tick:        tick,
		Liquidity:   liquidity,
		Token0Price: token0Price,
		Token1Price: token1Price,
	}, nil
}

type PoolDay struct {
	Date        time.Time
	Tick        int
	Liquidity   *big.Int
	Token0Price float32
	Token1Price float32
}

func NewPoolDay(client Client, pool *Pool, date time.Time) (*PoolDay, error) {
	var query poolDayDto
	timestamp := date.Unix() / secondsInDay
	err := client.Query(context.Background(), &query,
		map[string]any{
			"id": fmt.Sprintf("%s-%d", pool.Address, timestamp),
		})
	if err != nil {
		return nil, err
	}
	return query.fromDto()
}
