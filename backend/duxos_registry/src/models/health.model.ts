import { Schema, model } from 'mongoose';

export interface IHealth {
  nodeId: string;
  uptime: number;
  latency: number;
  lastCheck: Date;
}

const healthSchema = new Schema<IHealth>({
  nodeId: { type: String, required: true, unique: true },
  uptime: { type: Number, default: 0 },
  latency: { type: Number, default: 0 },
  lastCheck: { type: Date, default: Date.now },
});

export const Health = model<IHealth>('Health', healthSchema); 