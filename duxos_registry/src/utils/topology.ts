import { Node } from '../models/node.model';

export async function logInteraction(sourceNodeId: string, targetNodeId: string) {
  const source = await Node.findOne({ nodeId: sourceNodeId });
  const target = await Node.findOne({ nodeId: targetNodeId });
  if (!source || !target) {
    throw new Error('One or both nodes not found');
  }
  // Future: Store interaction in a dedicated model or graph database
  console.log(`Interaction logged: ${sourceNodeId} -> ${targetNodeId}`);
} 