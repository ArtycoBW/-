"use client";

import {
  Children,
  isValidElement,
  Fragment,
  type ReactNode,
  type InputHTMLAttributes,
} from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

type Option = { value: string; label: ReactNode; disabled?: boolean };
function optionsFrom(children: ReactNode): Option[] {
  return Children.toArray(children).flatMap((child): Option[] => {
    if (
      !isValidElement<{
        value?: string;
        disabled?: boolean;
        children?: ReactNode;
      }>(child)
    )
      return [];
    if (child.type === Fragment) return optionsFrom(child.props.children);
    return [
      {
        value: String(child.props.value ?? ""),
        label: child.props.children,
        disabled: child.props.disabled,
      },
    ];
  });
}

export function AppSelect({
  value,
  onChange,
  children,
  ...props
}: {
  value: string;
  onChange: (event: { target: { value: string } }) => void;
  children: ReactNode;
  "aria-label"?: string;
  id?: string;
  disabled?: boolean;
  required?: boolean;
  name?: string;
  className?: string;
}) {
  const options = optionsFrom(children);
  return (
    <Select
      value={value || "__all__"}
      onValueChange={(v) =>
        onChange({ target: { value: v === "__all__" ? "" : v } })
      }
      disabled={props.disabled}
      required={props.required}
      name={props.name}
    >
      <SelectTrigger
        id={props.id}
        aria-label={props["aria-label"]}
        className={`rz-select ${props.className || ""}`}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="rz-ui-popup" position="popper" sideOffset={6}>
        {options.map((option) => (
          <SelectItem
            key={option.value || "__all__"}
            value={option.value || "__all__"}
            disabled={option.disabled}
          >
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function AppCheckbox({
  checked,
  onChange,
  className,
  ...props
}: Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "onChange" | "value" | "size"
> & {
  onChange?: (event: { target: { checked: boolean } }) => void;
}) {
  return (
    <Checkbox
      id={props.id}
      name={props.name}
      checked={checked}
      required={props.required}
      disabled={props.disabled}
      aria-label={props["aria-label"]}
      className={`rz-checkbox ${className || ""}`}
      onCheckedChange={(v) => onChange?.({ target: { checked: v === true } })}
    />
  );
}
