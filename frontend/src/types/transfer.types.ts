export type TransferStatus =
  | 'idle'
  | 'pending_approval'
  | 'transferring'
  | 'paused'
  | 'verifying'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface FileMetadata {
  id: string;
  name: string;
  size: number;
  type: string;
  lastModified: number;
  totalChunks: number;
  chunkSize: number;
  fileHash?: string;
}

export interface ChunkPacket {
  fileId: string;
  chunkIndex: number;
  data: ArrayBuffer;
}

export interface TransferProgress {
  fileId: string;
  transferredBytes: number;
  totalBytes: number;
  percent: number;
  speedBytesPerSec: number;
  etaSeconds: number;
  status: TransferStatus;
  receivedChunks: number[];
  errorMessage?: string;
}
