import React, { useRef, useState } from "react";
import {
  Box, Typography, Button, CircularProgress, Chip,
} from "@mui/material";
import { CloudUpload, Delete } from "@mui/icons-material";
import uploadApi from "../utils/api";

interface ImageUploadProps {
  /** Called with the uploaded image URLs (original, thumb, medium) */
  onUploaded: (urls: { original: string; thumb: string; medium: string }) => void;
  /** Called when the uploaded image is removed */
  onRemove?: () => void;
  /** Currently displayed image URL */
  currentImage?: string;
  /** Button label */
  label?: string;
  /** Max file size in bytes (default 10 MB) */
  maxSize?: number;
}

const ImageUpload: React.FC<ImageUploadProps> = ({
  onUploaded,
  onRemove,
  currentImage,
  label = "Upload Image",
  maxSize = 10 * 1024 * 1024,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const displayUrl = currentImage || preview;

  const handleFile = async (file: File) => {
    setError(null);

    // Validate type
    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowed.includes(file.type)) {
      setError(`Unsupported file type: ${file.type}. Use JPEG, PNG, WebP, or GIF.`);
      return;
    }

    // Validate size
    if (file.size > maxSize) {
      setError(`File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max: ${maxSize / 1024 / 1024} MB`);
      return;
    }

    // Show local preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);

    // Upload
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await uploadApi.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      onUploaded(data.urls);
      setError(null);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? ((err as { response: { data: { detail?: string } } }).response?.data?.detail || "Upload failed")
          : "Upload failed";
      setError(msg);
      setPreview(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleRemove = () => {
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
    onRemove?.();
  };

  return (
    <Box
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      sx={{
        border: "2px dashed",
        borderColor: displayUrl ? "primary.main" : "divider",
        borderRadius: 2,
        p: 2,
        textAlign: "center",
        bgcolor: displayUrl ? "action.hover" : "background.paper",
        transition: "border-color 0.2s",
        "&:hover": { borderColor: "primary.light" },
        cursor: "pointer",
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {uploading ? (
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
          <CircularProgress size={32} />
          <Typography variant="caption" color="text.secondary">Uploading...</Typography>
        </Box>
      ) : displayUrl ? (
        <Box>
          <Box
            component="img"
            src={displayUrl}
            alt="Preview"
            sx={{
              maxWidth: "100%",
              maxHeight: 200,
              borderRadius: 1,
              objectFit: "contain",
              mb: 1,
            }}
          />
          <Box sx={{ display: "flex", gap: 1, justifyContent: "center" }}>
            <Chip
              label="Change"
              size="small"
              icon={<CloudUpload sx={{ fontSize: 14 }} />}
              onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
            />
            <Chip
              label="Remove"
              size="small"
              color="error"
              icon={<Delete sx={{ fontSize: 14 }} />}
              onClick={(e) => { e.stopPropagation(); handleRemove(); }}
            />
          </Box>
        </Box>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1, py: 2 }}>
          <CloudUpload sx={{ fontSize: 40, color: "text.secondary" }} />
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="caption" color="text.disabled">
            Drag & drop or click to browse
          </Typography>
          <Typography variant="caption" color="text.disabled">
            JPEG, PNG, WebP, GIF — max {(maxSize / 1024 / 1024).toFixed(0)} MB
          </Typography>
        </Box>
      )}

      {error && (
        <Typography variant="caption" color="error" sx={{ mt: 1, display: "block" }}>
          {error}
        </Typography>
      )}
    </Box>
  );
};

export default ImageUpload;
