package subgraph

import (
	"context"
	"github.com/shurcooL/graphql"
)

type Client struct {
	*graphql.Client
}

func NewClient() Client {
	return Client{graphql.NewClient("https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", nil)}
}

type Paginated interface {
	Next(*map[string]any) error
	Enough() bool
	Append(...Paginated)
}

func (client *Client) QueryPaginated(response Paginated, newQuery func() Paginated, param map[string]any) (err error) {
	var result []Paginated

	for {
		var query = newQuery()
		err = client.Query(context.Background(), query, param)
		if err != nil {
			return err
		}

		result = append(result, query)
		if query.Enough() {
			break
		}

		err = query.Next(&param)
		if err != nil {
			return err
		}
	}

	response.Append(result...)
	return nil
}
