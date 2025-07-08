import { Schema, model } from 'mongoose';

export interface IReputation {
  nodeId: string;
  score: number;
  taskCount: number;
  lastUpdated: Date;
}

const reputationSchema = new Schema<IReputation>({
  nodeId: { type: String, required: true, unique: true },
  score: { type: Number, default: 0 },
  taskCount: { type: Number, default: 0 },
  lastUpdated: { type: Date, default: Date.now },
});

export const Reputation = model<IReputation>('Reputation', reputationSchema); 