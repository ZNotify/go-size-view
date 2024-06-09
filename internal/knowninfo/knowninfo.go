package knowninfo

import (
	"fmt"

	"github.com/ZxillyFork/gore"

	"github.com/Zxilly/go-size-analyzer/internal/entity"
	"github.com/Zxilly/go-size-analyzer/internal/section"
	"github.com/Zxilly/go-size-analyzer/internal/wrapper"
)

type VersionFlag struct {
	Leq118 bool
	Meq120 bool
}

type KnownInfo struct {
	Size      uint64
	BuildInfo *gore.BuildInfo
	Sects     *section.Store
	Deps      *Dependencies
	KnownAddr *entity.KnownAddr

	Coverage entity.AddrCoverage

	Gore    *gore.GoFile
	Wrapper wrapper.RawFileWrapper

	VersionFlag VersionFlag

	HasDWARF bool
}

func (k *KnownInfo) UpdateVersionFlag() VersionFlag {
	ver, err := k.Gore.GetCompilerVersion()
	if err != nil {
		// if we can't get build info, we assume it's go1.20 plus
		return VersionFlag{
			Leq118: false,
			Meq120: true,
		}
	}

	return VersionFlag{
		Leq118: gore.GoVersionCompare(ver.Name, "go1.18.10") <= 0,
		Meq120: gore.GoVersionCompare(ver.Name, "go1.20rc1") >= 0,
	}
}

func (k *KnownInfo) RequireModInfo() error {
	if k.BuildInfo == nil {
		return fmt.Errorf("no build info")
	}
	return nil
}
