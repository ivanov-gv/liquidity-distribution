package main

import (
	"context"
	"fmt"
	"github.com/shurcooL/graphql"
)

type PoolInfo struct {
	Pool struct {
		Tick graphql.String
	} `graphql:"pool(id: $id)"`
}

func main() {
	client := graphql.NewClient("https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", nil)
	var query PoolInfo
	variables := map[string]any{
		"id": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
	}
	err := client.Query(context.Background(), &query, variables)
	if err != nil {
		fmt.Printf("there is an error: %s\n", err)
	}
	fmt.Println(query.Pool.Tick)
}
