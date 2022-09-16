package model

import (
	"math/big"
	"time"
)

type Token struct {
	Decimals int
	Symbol   string
}

type PoolBase struct {
	Tick        int
	Liquidity   *big.Int
	Token0Price float32
	Token1Price float32
}

type Pool struct {
	PoolBase
	Address     string
	Token0      Token
	Token1      Token
	FeeTier     int
	TickSpacing int
}

type PoolDay struct {
	PoolBase
	Date time.Time
}

type PoolHour struct {
	PoolBase
	Date time.Time
}
