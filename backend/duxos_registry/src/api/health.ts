import { Router, Request, Response } from 'express';
import { updateHealth, getNodeHealth } from '../services/health.service';

const router = Router();

router.post('/heartbeat', async (req: Request, res: Response) => {
  try {
    const { nodeId, uptime, latency } = req.body;
    if (!nodeId) {
      return res.status(400).json({ error: 'Missing nodeId' });
    }
    try {
      const health = await updateHealth({ nodeId, uptime, latency });
      res.json(health);
    } catch (err: any) {
      if (err.message === 'Node not found') {
        return res.status(404).json({ error: 'Node not found' });
      }
      throw err;
    }
  } catch (error) {
    res.status(500).json({ error: 'Failed to process heartbeat' });
  }
});

router.get('/:nodeId', async (req: Request, res: Response) => {
  try {
    const health = await getNodeHealth(req.params.nodeId);
    if (!health) {
      return res.status(404).json({ error: 'Node not found' });
    }
    res.json(health);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve health' });
  }
});

export default router; 