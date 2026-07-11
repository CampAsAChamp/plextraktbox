import { Combobox, Pill, PillsInput, useCombobox } from "@mantine/core";
import type { JobRunStatus } from "../../api/jobs";
import { RUN_STATUS_OPTIONS } from "../../utils/runFilters";
import { RunStatusBadge, RunStatusOptionRow } from "./RunBadges";

type RunStatusMultiSelectProps = {
  label?: string;
  value: JobRunStatus[];
  onChange: (value: JobRunStatus[]) => void;
  clearable?: boolean;
  placeholder?: string;
};

export function RunStatusMultiSelect({
  label,
  value,
  onChange,
  clearable = false,
  placeholder = "All statuses",
}: RunStatusMultiSelectProps) {
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
  });

  function toggleStatus(status: JobRunStatus) {
    if (value.includes(status)) {
      onChange(value.filter((item) => item !== status));
      return;
    }
    onChange([...value, status]);
  }

  function removeStatus(status: JobRunStatus) {
    onChange(value.filter((item) => item !== status));
  }

  const showClear = clearable && value.length > 0;

  return (
    <Combobox
      store={combobox}
      onOptionSubmit={(optionValue) => toggleStatus(optionValue as JobRunStatus)}
    >
      <Combobox.DropdownTarget>
        <PillsInput
          label={label}
          pointer
          onClick={() => combobox.toggleDropdown()}
          __defaultRightSection={<Combobox.Chevron />}
          __clearSection={<Combobox.ClearButton onClear={() => onChange([])} />}
          __clearable={showClear}
          rightSectionPointerEvents={showClear ? "all" : "none"}
          styles={{
            input: { cursor: "pointer" },
            section: { cursor: "pointer" },
          }}
        >
          <Pill.Group>
            {value.map((status) => (
              <RunStatusBadge key={status} status={status} onRemove={() => removeStatus(status)} />
            ))}
            <Combobox.EventsTarget>
              <PillsInput.Field
                placeholder={value.length === 0 ? placeholder : undefined}
                type={value.length === 0 ? "visible" : "hidden"}
                style={
                  value.length > 0
                    ? { flex: "0 0 0", width: 0, minWidth: 0, padding: 0, overflow: "hidden" }
                    : undefined
                }
                readOnly
                pointer
                onBlur={() => combobox.closeDropdown()}
                onKeyDown={(event) => {
                  if (event.key === "Backspace" && value.length > 0) {
                    removeStatus(value[value.length - 1]);
                  }
                  if (event.key === " ") {
                    event.preventDefault();
                    combobox.toggleDropdown();
                  }
                }}
              />
            </Combobox.EventsTarget>
          </Pill.Group>
        </PillsInput>
      </Combobox.DropdownTarget>

      <Combobox.Dropdown>
        <Combobox.Options>
          {RUN_STATUS_OPTIONS.map((option) => {
            const checked = value.includes(option.value);
            return (
              <Combobox.Option key={option.value} value={option.value} active={checked}>
                <RunStatusOptionRow status={option.value} checked={checked} />
              </Combobox.Option>
            );
          })}
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
}
