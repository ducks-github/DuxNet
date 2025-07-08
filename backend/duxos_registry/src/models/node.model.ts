import { Schema, model } from 'mongoose';

export interface INode {
  nodeId: string;
  address: string;
  port: number;
  status: 'active' | 'inactive' | 'pending';
  registeredAt: Date;
  lastSeen: Date;
}

const nodeSchema = new Schema<INode>({
  nodeId: { type: String, required: true, unique: true },
  address: { type: String, required: true },
  port: { type: Number, required: true },
  status: { type: String, enum: ['active', 'inactive', 'pending'], default: 'pending' },
  registeredAt: { type: Date, default: Date.now },
  lastSeen: { type: Date, default: Date.now },
});

export const Node = model<INode>('Node', nodeSchema); 