import { Box } from "@mantine/core";

export type JsonTokenKind =
  | "key"
  | "string"
  | "number"
  | "boolean"
  | "null"
  | "punctuation"
  | "text";

export type JsonToken = {
  kind: JsonTokenKind;
  text: string;
};

export const JSON_SYNTAX_COLORS: Record<JsonTokenKind, string> = {
  key: "#9cdcfe",
  string: "#ce9178",
  number: "#b5cea8",
  boolean: "#569cd6",
  null: "#569cd6",
  punctuation: "#808080",
  text: "inherit",
};

const TOKEN_PATTERN =
  /"(?:\\.|[^"\\])*"\s*:|"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\btrue\b|\bfalse\b|\bnull\b|[{}\[\],]|[^\S\n]+|\n/g;

export function tokenizeJsonText(text: string): JsonToken[] {
  const tokens: JsonToken[] = [];
  let index = 0;

  for (const match of text.matchAll(TOKEN_PATTERN)) {
    const start = match.index ?? 0;
    if (start > index) {
      tokens.push({ kind: "text", text: text.slice(index, start) });
    }

    const raw = match[0];
    if (raw.endsWith(":")) {
      tokens.push({ kind: "key", text: raw });
    } else if (raw.startsWith('"')) {
      tokens.push({ kind: "string", text: raw });
    } else if (raw === "true" || raw === "false") {
      tokens.push({ kind: "boolean", text: raw });
    } else if (raw === "null") {
      tokens.push({ kind: "null", text: raw });
    } else if (/^-?\d/.test(raw)) {
      tokens.push({ kind: "number", text: raw });
    } else if (/^\s+$/.test(raw) || raw === "\n") {
      tokens.push({ kind: "text", text: raw });
    } else {
      tokens.push({ kind: "punctuation", text: raw });
    }

    index = start + raw.length;
  }

  if (index < text.length) {
    tokens.push({ kind: "text", text: text.slice(index) });
  }

  return tokens;
}

type ColoredJsonSpansProps = {
  value: string;
};

export function ColoredJsonSpans({ value }: ColoredJsonSpansProps) {
  const tokens = tokenizeJsonText(value);

  return (
    <>
      {tokens.map((token, index) => (
        <Box
          key={`${index}-${token.text}`}
          component="span"
          style={{ color: JSON_SYNTAX_COLORS[token.kind] }}
        >
          {token.text}
        </Box>
      ))}
    </>
  );
}

type ColoredJsonProps = {
  value: string;
};

export function ColoredJson({ value }: ColoredJsonProps) {
  return (
    <Box
      component="pre"
      m={0}
      p="xs"
      style={{
        fontSize: 12,
        lineHeight: 1.4,
        overflowX: "auto",
        whiteSpace: "pre",
        background: "var(--mantine-color-dark-6)",
        borderRadius: 4,
      }}
    >
      <ColoredJsonSpans value={value} />
    </Box>
  );
}
