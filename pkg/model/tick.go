package model

import "math/big"

type Tick struct {
	TickIdx      int
	LiquidityNet *big.Int
}
