package utils

import (
	"debug/gosym"
	"reflect"
	"testing"
	"unsafe"

	"github.com/stretchr/testify/assert"
)

func TestUglyGuess(t *testing.T) {
	tests := []struct {
		name   string
		symbol string
		want   string
	}{
		{
			"atlas",
			"ariga.io/atlas/sql/sqlclient.(*Tx).database/sql.grabConn",
			"ariga.io/atlas/sql/sqlclient",
		},
		{
			"ZNotify",
			"github.com/ZNotify/server/app/api/common.(*Context).github.com/gin-gonic/gin.reset",
			"github.com/ZNotify/server/app/api/common",
		},
		{
			"protobuf",
			"github.com/gogo/protobuf/protoc-gen-gogo/descriptor.(*FieldOptions).github.com/gogo/protobuf/proto.extensionsRead",
			"github.com/gogo/protobuf/protoc-gen-gogo/descriptor",
		},
		{
			"protobuf no pointer",
			"github.com/gogo/protobuf/protoc-gen-gogo/descriptor.FileOptions.github.com/gogo/protobuf/proto.extensionsWrite",
			"github.com/gogo/protobuf/protoc-gen-gogo/descriptor",
		},
		{
			"path contains domain",
			"github.com/prometheus/common/internal/bitbucket.org/ww/goautoneg.accept_slice.Len",
			"github.com/prometheus/common/internal/bitbucket.org/ww/goautoneg",
		},
		{
			"path contains domain multi dots",
			"go.opentelemetry.io/contrib/instrumentation/go.mongodb.org/mongo-driver/mongo/otelmongo.(*Cursor).Next",
			"go.opentelemetry.io/contrib/instrumentation/go.mongodb.org/mongo-driver/mongo/otelmongo",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			sym := &gosym.Sym{
				Name: tt.symbol,
			}

			// ugly trick to set goVersion
			val := reflect.ValueOf(sym).Elem()
			ver := val.FieldByName("goVersion")
			reflect.NewAt(ver.Type(), unsafe.Pointer(ver.UnsafeAddr())).Elem().SetInt(int64(5))

			firstPass := sym.PackageName()
			assert.Equalf(t, tt.want, UglyGuess(firstPass), "UglyGuess(%v)", tt.symbol)
		})
	}
}

func TestPrefixToPath(t *testing.T) {
	var escapeTests = []struct {
		Path    string
		Escaped string
	}{
		{"foo/bar/v1", "foo/bar/v1"},
		{"foo/bar/v.1", "foo/bar/v%2e1"},
		{"f.o.o/b.a.r/v1", "f.o.o/b.a.r/v1"},
		{"f.o.o/b.a.r/v.1", "f.o.o/b.a.r/v%2e1"},
		{"f.o.o/b.a.r/v..1", "f.o.o/b.a.r/v%2e%2e1"},
		{"f.o.o/b.a.r/v..1.", "f.o.o/b.a.r/v%2e%2e1%2e"},
		{"f.o.o/b.a.r/v%1", "f.o.o/b.a.r/v%251"},
		{"runtime", "runtime"},
		{"sync/atomic", "sync/atomic"},
		{"golang.org/x/tools/godoc", "golang.org/x/tools/godoc"},
		{"foo.bar/baz.quux", "foo.bar/baz%2equux"},
		{"", ""},
		{"%foo%bar", "%25foo%25bar"},
		{"\x01\x00\x7F☺", "%01%00%7f%e2%98%ba"},
	}
	for _, tc := range escapeTests {
		got, err := PrefixToPath(tc.Escaped)
		if err != nil {
			t.Errorf("expected PrefixToPath(%s) err = nil, got %v", tc.Escaped, err)
		}
		if got != tc.Path {
			t.Errorf("expected PrefixToPath(%s) = %s, got %s", tc.Escaped, tc.Path, got)
		}
	}
}
