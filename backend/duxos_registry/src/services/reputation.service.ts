import { Reputation } from '../models/reputation.model';
import { Node } from '../models/node.model';

export async function updateReputation(nodeId: string, taskSuccess: boolean) {
  const node = await Node.findOne({ nodeId });
  if (!node) {
    throw new Error('Node not found');
  }

  const reputation = await Reputation.findOneAndUpdate(
    { nodeId },
    {
      $inc: { score: taskSuccess ? 10 : -5, taskCount: 1 },
      $set: { lastUpdated: new Date() },
    },
    { upsert: true, new: true }
  );
  return reputation;
} 