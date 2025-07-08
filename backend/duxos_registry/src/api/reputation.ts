import { Router } from 'express';
import { updateReputation } from '../services/reputation.service';

const router = Router();

router.post('/update', async (req, res) => {
  try {
    const { nodeId, taskSuccess } = req.body;
    if (!nodeId) {
      return res.status(400).json({ error: 'Missing nodeId' });
    }
    const reputation = await updateReputation(nodeId, taskSuccess);
    res.json(reputation);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update reputation' });
  }
});

export default router; 