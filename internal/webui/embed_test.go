package webui_test

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"golang.org/x/net/html"

	"github.com/Zxilly/go-size-analyzer/internal/printer"
	"github.com/Zxilly/go-size-analyzer/internal/webui"
)

func TestGetTemplate(t *testing.T) {
	got := webui.GetTemplate()

	// Should contain printer.ReplacedStr
	assert.Contains(t, got, printer.ReplacedStr)

	// Should html
	_, err := html.Parse(strings.NewReader(got))
	require.NoError(t, err)
}
