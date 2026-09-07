import React, { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';

interface UploadAreaProps {
  onFileSelect: (file: File) => void;
  acceptedFormats?: string[];
  className?: string;
}

export function UploadArea({ 
  onFileSelect, 
  acceptedFormats = ['MP4', 'MOV', 'AVI'],
  className = ''
}: UploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`cursor-pointer border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center transition-colors text-center ${
        isDragging ? 'border-blue-500 bg-blue-500/5' : 'border-navy-600 hover:border-blue-500 hover:bg-blue-500/5'
      } ${className}`}
    >
      <input 
        type="file" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileChange}
        accept={acceptedFormats.map(fmt => `.${fmt.toLowerCase()}`).join(',')}
      />
      <div className="bg-navy-800 p-4 rounded-full mb-4">
        <UploadCloud className="w-8 h-8 text-blue-500" />
      </div>
      <h3 className="text-lg font-medium text-slate-200 mb-2">Click or drag file to upload</h3>
      <p className="text-sm text-slate-400">
        Accepted formats: {acceptedFormats.join(', ')}
      </p>
    </div>
  );
}
