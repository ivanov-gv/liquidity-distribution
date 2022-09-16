package subgraph

const (
	// Limit for subgraph select queries
	limit        = 1000
	secondsInDay = 86400
)

type OrderDirection string

const (
	Ascending  OrderDirection = "asc"
	Descending OrderDirection = "desc"
)
