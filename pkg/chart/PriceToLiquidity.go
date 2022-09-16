package chart

import (
	"github.com/ivanov-gv/liquidity-distribution/pkg/convert"
	"github.com/ivanov-gv/liquidity-distribution/pkg/model"
	"math/big"
)

type PriceLiquidity struct {
	Price     []float64
	Liquidity []float64
}

func reverse[T any](a []T) {
	for left, right := 0, len(a)-1; left < right; left, right = left+1, right-1 {
		a[left], a[right] = a[right], a[left]
	}
}

func TickToLiquidityPrice(lowerTicks []model.Tick, upperTicks []model.Tick, numSurroundingTicks int,
	pool model.Pool) PriceLiquidity {

	activeTick := convert.ActiveTick(pool.Tick, pool.TickSpacing)
	if activeTick < convert.MinTick {
		activeTick = convert.MinTick
	} else if activeTick > convert.MaxTick {
		activeTick = convert.MaxTick
	}

	activeTickPriceToken0 := convert.TickToPriceToken0(activeTick, pool.Token0.Decimals, pool.Token1.Decimals)
	liquidityAdjActiveTickToken0, liquidityAdjActiveTickToken1 := convert.LiquidityToToken0Token1(pool.Liquidity,
		activeTick, activeTick+pool.TickSpacing,
		pool.Token0.Decimals, pool.Token1.Decimals)

	type tickProcessed struct {
		tick               int
		priceToken0        float64
		priceToken1        float64
		liquidityRaw       *big.Int
		liquidityNet       *big.Int
		liquidityAdjToken0 float64
		liquidityAdjToken1 float64
	}

	currentTick := tickProcessed{
		tick:               activeTick,
		priceToken0:        activeTickPriceToken0,
		priceToken1:        1 / activeTickPriceToken0,
		liquidityRaw:       pool.Liquidity,
		liquidityNet:       new(big.Int),
		liquidityAdjToken0: liquidityAdjActiveTickToken0,
		liquidityAdjToken1: liquidityAdjActiveTickToken1,
	}

	if upperTicks[0].TickIdx == currentTick.tick {
		currentTick.liquidityNet = upperTicks[0].LiquidityNet
	}

	type Direction uint8
	const (
		Ascending Direction = iota
		Descending
	)

	computeSurroundingTicks := func(activeTick tickProcessed, direction Direction, initializedTicks []model.Tick, resultChan chan []tickProcessed) {
		previousTickProcessed := activeTick
		processedTicks := make([]tickProcessed, numSurroundingTicks)

		for i := 0; i < numSurroundingTicks; i++ {
			var currentTickIdx int
			if direction == Ascending {
				currentTickIdx = previousTickProcessed.tick + pool.TickSpacing
			} else { // Descending
				currentTickIdx = previousTickProcessed.tick - pool.TickSpacing
			}

			if currentTickIdx < convert.MinTick || currentTickIdx > convert.MaxTick {
				break
			}

			priceToken0 := convert.TickToPriceToken0(currentTickIdx, pool.Token0.Decimals, pool.Token1.Decimals)
			currentTickProcessed := tickProcessed{
				tick:               currentTickIdx,
				priceToken0:        priceToken0,
				priceToken1:        1 / priceToken0,
				liquidityRaw:       previousTickProcessed.liquidityRaw,
				liquidityNet:       new(big.Int),
				liquidityAdjToken0: 0,
				liquidityAdjToken1: 0,
			}

			if initializedTicks[0].TickIdx == currentTickProcessed.tick {
				currentTickProcessed.liquidityNet = initializedTicks[0].LiquidityNet
				initializedTicks = initializedTicks[1:]
			}

			// Update liquidity
			if direction == Ascending && currentTickProcessed.liquidityNet.Cmp(new(big.Int)) != 0 {
				currentTickProcessed.liquidityRaw = new(big.Int).Add(
					previousTickProcessed.liquidityRaw,
					currentTickProcessed.liquidityNet)
			} else if direction == Descending && previousTickProcessed.liquidityNet.Cmp(new(big.Int)) != 0 {
				// We are iterating descending, so look at the previous tick and apply any net liquidity.
				currentTickProcessed.liquidityRaw = new(big.Int).Sub(
					previousTickProcessed.liquidityRaw,
					previousTickProcessed.liquidityNet,
				)
			}

			currentTickProcessed.liquidityAdjToken0, currentTickProcessed.liquidityAdjToken1 =
				convert.LiquidityToToken0Token1(pool.Liquidity,
					currentTickProcessed.tick, currentTickProcessed.tick+pool.TickSpacing,
					pool.Token0.Decimals, pool.Token1.Decimals)

			processedTicks = append(processedTicks, currentTickProcessed)
			previousTickProcessed = currentTickProcessed
		}

		resultChan <- processedTicks
		close(resultChan)
	}

	upperTicksChan := make(chan []tickProcessed)
	go computeSurroundingTicks(currentTick, Ascending, upperTicks, upperTicksChan)
	lowerTicksChan := make(chan []tickProcessed)
	go computeSurroundingTicks(currentTick, Descending, lowerTicks, lowerTicksChan)

	lowerTicksProcessed := <-lowerTicksChan
	upperTicksProcessed := <-upperTicksChan

	reverse(lowerTicksProcessed)

	// TODO: return prices and liquidity
}
