import type { ReactNode } from "react";
import React, { useEffect, useMemo } from "react";
import { useAsync } from "react-use";
import { Box, Dialog, DialogContent, DialogContentText, DialogTitle } from "@mui/material";
import { createEntry } from "../tool/entry.ts";
import TreeMap from "../treemap/TreeMap.tsx";
import { GsaInstance } from "../worker/helper.ts";
import { FileSelector } from "./FileSelector.tsx";

type ModalState = {
  isOpen: false;
} | {
  isOpen: true;
  title: string;
  content: ReactNode;
};

const LogViewer: React.FC<{ log: string }> = ({ log }) => {
  return (
    <Box
      style={{
        maxHeight: "50vh",
        minHeight: "10vh",
        overflowY: "auto",
      }}
      fontFamily="monospace"
      component="pre"
    >
      {log}
    </Box>
  );
};

export const Explorer: React.FC = () => {
  const [log, setLog] = React.useState<string>("");

  const { value: analyzer, loading, error: loadError } = useAsync(async () => {
    return GsaInstance.create((line) => {
      setLog(prev => `${prev + line}\n`);
      console.info(line);
    });
  });

  const [file, setFile] = React.useState<File | null>(null);

  const [modalState, setModalState] = React.useState<ModalState>({ isOpen: false });

  const { value: result, loading: analyzing } = useAsync(async () => {
    if (!file || !analyzer) {
      return;
    }

    const bytes = await file.arrayBuffer();
    const uint8 = new Uint8Array(bytes);

    return analyzer.analyze(file.name, uint8);
  }, [file]);

  const entry = useMemo(() => {
    if (!result) {
      return null;
    }

    return createEntry(result);
  }, [result]);

  useEffect(() => {
    if (loadError || (!analyzer && !loading)) {
      setModalState({
        isOpen: true,
        title: "Error",
        content:
          <>
            <DialogContentText>
              Failed to load WebAssembly module
            </DialogContentText>
            {loadError && <DialogContentText>{loadError.message}</DialogContentText>}
          </>,
      });
    }
    else if (loading) {
      setModalState({
        isOpen: true,
        title: "Loading",
        content:
          <DialogContentText>Loading WebAssembly module...</DialogContentText>,
      });
    }
    else if (!file) {
      setModalState({
        isOpen: true,
        title: "Select a go binary",
        content: (
          <FileSelector handler={(file) => {
            setFile(file);
          }}
          />
        ),
      });
    }
    else if (analyzing) {
      setModalState({
        isOpen: true,
        title: `Analyzing ${file.name}`,
        content: (
          <LogViewer log={log} />
        ),
      });
    }
    else if (!analyzing && !result && !entry) {
      setModalState({
        isOpen: true,
        title: `Failed to analyze ${file.name}`,
        content: (
          <LogViewer log={log} />
        ),
      });
    }
    else {
      setModalState({ isOpen: false });
    }
  }, [loadError, loading, file, result, analyzing, entry, analyzer, log]);

  return (
    <>
      <Dialog
        open={modalState.isOpen}
      >
        <DialogTitle>{modalState.isOpen && modalState.title}</DialogTitle>
        <DialogContent dividers>
          {modalState.isOpen && modalState.content}
        </DialogContent>
      </Dialog>
      {entry && <TreeMap entry={entry} />}
    </>
  );
};
