package subgraph

const (
	secondsInDay = 86400
	MaxTick      = 887272
	MinTick      = -MaxTick
)

type OrderDirection string

const (
	Ascending  OrderDirection = "asc"
	Descending OrderDirection = "desc"
)

// Limit for subgraph select queries
const limit = 1000
