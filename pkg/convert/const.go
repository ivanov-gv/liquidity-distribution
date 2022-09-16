package convert

var feeTierToTickSpacing = map[int]int{
	100:   1,
	500:   10,
	3000:  60,
	10000: 200,
}

const (
	MaxTick = 887272
	MinTick = -MaxTick
)
