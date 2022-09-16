package convert

import (
	"math"
	"math/big"
)

func FeeTierToTickSpacing(feeTier int) int {
	return feeTierToTickSpacing[feeTier]
}

func FeeTierToFeePercent(feeTier int) float64 {
	return float64(feeTier) / 10000.0
}

func TickToRawPriceToken0(tick int) float64 {
	return math.Pow(1.0001, float64(tick))
}

func RawPriceToPriceToken0(decimalsToken0 int, decimalsToken1 int, rawPriceToken0 float64) float64 {
	return math.Pow(10.0, float64(decimalsToken1-decimalsToken0)) / rawPriceToken0
}

func TickToPriceToken0(tick int, decimalsToken0 int, decimalsToken1 int) float64 {
	return RawPriceToPriceToken0(decimalsToken0, decimalsToken1, TickToRawPriceToken0(tick))
}

func ActiveTick(currentTick int, tickSpacing int) int {
	return (currentTick / tickSpacing) * tickSpacing
}

func LiquidityToToken0Token1(liquidity *big.Int, lowerTick int, upperTick int,
	decimals0 int, decimals1 int) (float64, float64) {
	// Compute square roots of prices corresponding to the bottom and top ticks
	sqrtPriceA := TickToRawPriceToken0(lowerTick / 2) // price = 1.0001 ** tick i.e.
	sqrtPriceB := TickToRawPriceToken0(upperTick / 2) // sqrt(price) = 1.0001 ** (tick // 2)

	// Compute virtual amounts of the two assets
	// amount0 = liquidity * (sqrt_price_b - sqrt_price_a) / (sqrt_price_a * sqrt_price_b)
	amount0 := new(big.Float).Mul(new(big.Float).SetInt(liquidity), new(big.Float).SetFloat64((sqrtPriceB-sqrtPriceA)/(sqrtPriceA*sqrtPriceB)))
	// amount1 = liquidity * (sqrt_price_b - sqrt_price_a)
	amount1 := new(big.Float).Mul(new(big.Float).SetInt(liquidity), new(big.Float).SetFloat64(sqrtPriceB-sqrtPriceA))

	// Compute adjusted amount
	//  adjAmount0_Big := amount0 / math.Pow(10, float64(decimals0))
	adjAmount0 := new(big.Float).Quo(amount0, new(big.Float).SetFloat64(math.Pow(10, float64(decimals0))))
	// 	adjAmount1 := amount1 / math.Pow(10, decimals1)
	adjAmount1 := new(big.Float).Quo(amount1, new(big.Float).SetFloat64(math.Pow(10, float64(decimals1))))

	_adjAmount0, _ := adjAmount0.Float64()
	_adjAmount1, _ := adjAmount1.Float64()
	return _adjAmount0, _adjAmount1
}

//func RoundTimestampToDay(timestamp int) int {
//	return (timestamp / 86400) * 86400
//}
