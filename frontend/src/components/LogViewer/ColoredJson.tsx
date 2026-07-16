import { Box } from "@mantine/core"

import { JSON_SYNTAX_COLORS, tokenizeJsonText } from "src/components/LogViewer/jsonTokens"

type ColoredJsonSpansProps = {
  value: string
}

export function ColoredJsonSpans({ value }: ColoredJsonSpansProps) {
  const tokens = tokenizeJsonText(value)

  return (
    <>
      {tokens.map((token, index) => (
        <Box key={`${index}-${token.text}`} component="span" style={{ color: JSON_SYNTAX_COLORS[token.kind] }}>
          {token.text}
        </Box>
      ))}
    </>
  )
}

type ColoredJsonProps = {
  value: string
}

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
        borderRadius: "var(--mantine-radius-md)",
      }}
    >
      <ColoredJsonSpans value={value} />
    </Box>
  )
}
