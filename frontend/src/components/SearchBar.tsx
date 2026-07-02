import React, { useState, useEffect, useRef } from "react";
import { TextField, InputAdornment, IconButton } from "@mui/material";
import { Search as SearchIcon, Clear } from "@mui/icons-material";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  fullWidth?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = "Search…",
  debounceMs = 300,
  fullWidth = false,
}) => {
  const [local, setLocal] = useState(value);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  // Sync external value changes
  useEffect(() => {
    setLocal(value);
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setLocal(v);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => onChange(v), debounceMs);
  };

  const handleClear = () => {
    setLocal("");
    if (timerRef.current) clearTimeout(timerRef.current);
    onChange("");
  };

  return (
    <TextField
      size="small"
      fullWidth={fullWidth}
      placeholder={placeholder}
      value={local}
      onChange={handleChange}
      sx={{ minWidth: { xs: 1, sm: 220 } }}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon fontSize="small" color="action" />
          </InputAdornment>
        ),
        endAdornment: local ? (
          <InputAdornment position="end">
            <IconButton size="small" onClick={handleClear} edge="end">
              <Clear fontSize="small" />
            </IconButton>
          </InputAdornment>
        ) : undefined,
      }}
    />
  );
};

export default SearchBar;
