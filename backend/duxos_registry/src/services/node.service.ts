import { Node } from '../models/node.model';
import { INode } from '../models/node.model';

export async function registerNode(data: {
  nodeId: string;
  address: string;
  port: number;
}): Promise<INode> {
  const existingNode = await Node.findOne({ nodeId: data.nodeId });
  if (existingNode) {
    throw new Error('Node already registered');
  }
  const node = new Node({
    nodeId: data.nodeId,
    address: data.address,
    port: data.port,
    status: 'active',
  });
  return await node.save();
} 