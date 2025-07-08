import request from 'supertest';
import express from 'express';
import nodeRouter from '../src/api/node';
import { Node } from '../src/models/node.model';

jest.mock('../src/models/node.model');

const app = express();
app.use(express.json());
app.use('/nodes', nodeRouter);

describe('Node Discovery API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should list all active nodes', async () => {
    (Node.find as jest.Mock).mockReturnValue({ select: jest.fn().mockResolvedValue([
      { nodeId: 'node1', address: '127.0.0.1', port: 3001 },
      { nodeId: 'node2', address: '127.0.0.2', port: 3002 },
    ]) });

    const res = await request(app)
      .get('/nodes/discover');
    expect(res.status).toBe(200);
    expect(res.body.length).toBe(2);
    expect(res.body[0].nodeId).toBe('node1');
    expect(res.body[1].nodeId).toBe('node2');
  });

  it('should handle errors gracefully', async () => {
    (Node.find as jest.Mock).mockImplementation(() => { throw new Error('DB error'); });

    const res = await request(app)
      .get('/nodes/discover');
    expect(res.status).toBe(500);
    expect(res.body.error).toBe('Failed to discover nodes');
  });
}); 