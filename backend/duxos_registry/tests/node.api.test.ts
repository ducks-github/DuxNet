import request from 'supertest';
import express from 'express';
import nodeRouter from '../src/api/node';
import { Node } from '../src/models/node.model';

jest.mock('../src/models/node.model');

const app = express();
app.use(express.json());
app.use('/nodes', nodeRouter);

describe('Node Registration API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should register a new node successfully', async () => {
    (Node.findOne as jest.Mock).mockResolvedValue(null);
    (Node.prototype.save as jest.Mock).mockResolvedValue({
      nodeId: 'node1', address: '127.0.0.1', port: 3001, status: 'active', registeredAt: new Date(), lastSeen: new Date()
    });

    const res = await request(app)
      .post('/nodes/register')
      .send({ nodeId: 'node1', address: '127.0.0.1', port: 3001 });
    expect(res.status).toBe(201);
    expect(res.body.nodeId).toBe('node1');
  });

  it('should return error for duplicate node registration', async () => {
    (Node.findOne as jest.Mock).mockResolvedValue({ nodeId: 'node1' });

    const res = await request(app)
      .post('/nodes/register')
      .send({ nodeId: 'node1', address: '127.0.0.1', port: 3001 });
    expect(res.status).toBe(500);
    expect(res.body.error).toBe('Failed to register node');
  });
}); 