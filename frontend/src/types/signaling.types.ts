export type PeerConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'failed';

export type SignalingMessageType =
  | 'join_room'
  | 'peer_joined'
  | 'peer_left'
  | 'offer'
  | 'answer'
  | 'ice_candidate'
  | 'transfer_request'
  | 'transfer_accepted'
  | 'transfer_rejected'
  | 'transfer_resume_request'
  | 'transfer_resume_ack';

export interface SignalingMessage<T = unknown> {
  type: SignalingMessageType;
  roomId: string;
  senderId: string;
  payload: T;
}
