import { Combobox, Pill, PillsInput, useCombobox } from "@mantine/core"

import { LOG_LEVEL_OPTIONS, type LogLevel, LogLevelBadge, LogLevelOptionRow } from "src/components/LogViewer/logLevels"

type LogLevelMultiSelectProps = {
  label?: string
  value: LogLevel[]
  onChange: (value: LogLevel[]) => void
  clearable?: boolean
  placeholder?: string
}

export function LogLevelMultiSelect({ label, value, onChange, clearable = false, placeholder = "All levels" }: LogLevelMultiSelectProps) {
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
  })

  function toggleLevel(level: LogLevel) {
    if (value.includes(level)) {
      onChange(value.filter((item) => item !== level))
      return
    }
    onChange([...value, level])
  }

  function removeLevel(level: LogLevel) {
    onChange(value.filter((item) => item !== level))
  }

  const showClear = clearable && value.length > 0

  return (
    <Combobox store={combobox} onOptionSubmit={(optionValue) => toggleLevel(optionValue as LogLevel)}>
      <Combobox.DropdownTarget>
        <PillsInput
          label={label}
          pointer
          onClick={() => combobox.toggleDropdown()}
          __defaultRightSection={<Combobox.Chevron />}
          __clearSection={<Combobox.ClearButton onClear={() => onChange([])} />}
          __clearable={showClear}
          rightSectionPointerEvents={showClear ? "all" : "none"}
          w={{ base: "100%", sm: 220 }}
          styles={{
            input: { cursor: "pointer" },
            section: { cursor: "pointer" },
          }}
        >
          <Pill.Group>
            {value.map((level) => (
              <LogLevelBadge key={level} level={level} onRemove={() => removeLevel(level)} />
            ))}
            <Combobox.EventsTarget>
              <PillsInput.Field
                placeholder={value.length === 0 ? placeholder : undefined}
                type={value.length === 0 ? "visible" : "hidden"}
                style={value.length > 0 ? { flex: "0 0 0", width: 0, minWidth: 0, padding: 0, overflow: "hidden" } : undefined}
                readOnly
                pointer
                onBlur={() => combobox.closeDropdown()}
                onKeyDown={(event) => {
                  if (event.key === "Backspace" && value.length > 0) {
                    removeLevel(value[value.length - 1])
                  }
                  if (event.key === " ") {
                    event.preventDefault()
                    combobox.toggleDropdown()
                  }
                }}
              />
            </Combobox.EventsTarget>
          </Pill.Group>
        </PillsInput>
      </Combobox.DropdownTarget>

      <Combobox.Dropdown>
        <Combobox.Options>
          {LOG_LEVEL_OPTIONS.map((option) => {
            const checked = value.includes(option.value)
            return (
              <Combobox.Option key={option.value} value={option.value} active={checked}>
                <LogLevelOptionRow level={option.value} checked={checked} />
              </Combobox.Option>
            )
          })}
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  )
}
