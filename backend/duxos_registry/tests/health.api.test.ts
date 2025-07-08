import request from 'supertest';
import express from 'express';
import healthRouter from '../src/api/health';
import { Health } from '../src/models/health.model';
import { Node } from '../src/models/node.model';

jest.mock('../src/models/health.model');
jest.mock('../src/models/node.model');

const app = express();
app.use(express.json());
app.use('/health', healthRouter);

describe('Health Monitoring API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update health data for a node', async () => {
    (Node.findOne as jest.Mock).mockResolvedValue({ nodeId: 'node1', lastSeen: new Date(), save: jest.fn() });
    (Health.findOneAndUpdate as jest.Mock).mockResolvedValue({ nodeId: 'node1', uptime: 100, latency: 10, lastCheck: new Date() });

    const res = await request(app)
      .post('/health/heartbeat')
      .send({ nodeId: 'node1', uptime: 100, latency: 10 });
    expect(res.status).toBe(200);
    expect(res.body.nodeId).toBe('node1');
    expect(res.body.uptime).toBe(100);
    expect(res.body.latency).toBe(10);
  });

  it('should return error if node does not exist', async () => {
    (Node.findOne as jest.Mock).mockResolvedValue(null);

    const res = await request(app)
      .post('/health/heartbeat')
      .send({ nodeId: 'nodeX', uptime: 100, latency: 10 });
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('Node not found');
  });
}); 