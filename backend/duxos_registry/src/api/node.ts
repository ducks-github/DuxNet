import { Router } from 'express';
import { Node } from '../models/node.model';
import { registerNode } from '../services/node.service';

const router = Router();

router.post('/register', async (req, res) => {
  try {
    const { nodeId, address, port } = req.body;
    if (!nodeId || !address || !port) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    const node = await registerNode({ nodeId, address, port });
    res.status(201).json(node);
  } catch (error) {
    res.status(500).json({ error: 'Failed to register node' });
  }
});

router.get('/discover', async (req, res) => {
  try {
    const nodes = await Node.find({ status: 'active' }).select('nodeId address port');
    res.json(nodes);
  } catch (error) {
    res.status(500).json({ error: 'Failed to discover nodes' });
  }
});

export default router; 