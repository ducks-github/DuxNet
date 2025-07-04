import { Health } from '../models/health.model';
import { Node } from '../models/node.model';

export async function updateHealth(data: {
  nodeId: string;
  uptime?: number;
  latency?: number;
}) {
  const node = await Node.findOne({ nodeId: data.nodeId });
  if (!node) {
    throw new Error('Node not found');
  }
  node.lastSeen = new Date();
  await node.save();

  const health = await Health.findOneAndUpdate(
    { nodeId: data.nodeId },
    {
      $set: {
        uptime: data.uptime || 0,
        latency: data.latency || 0,
        lastCheck: new Date(),
      },
    },
    { upsert: true, new: true }
  );
  return health;
}

export async function getNodeHealth(nodeId: string) {
  return await Health.findOne({ nodeId });
} 