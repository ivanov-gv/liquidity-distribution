package main

import (
	"fmt"
	"github.com/ivanov-gv/liquidity-distribution/pkg/subgraph"
	"github.com/shurcooL/graphql"
	"time"
)

func main() {
	client := graphql.NewClient("https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", nil)
	pool, err := subgraph.NewPool(client, "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8")
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(pool)
	poolDayData, err := subgraph.NewPoolDay(client, pool, time.Date(2022, 1, 1, 0, 0, 0, 0, time.Local))
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(poolDayData)

	ticks, err := subgraph.GetTicksForNow(client, pool, 10000000, -100000000)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(ticks)
}
