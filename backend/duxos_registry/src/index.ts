import express from 'express';
import mongoose from 'mongoose';
import nodeRouter from './api/node';
import healthRouter from './api/health';
import reputationRouter from './api/reputation';
import { dbConnect } from './config/db';

const app = express();
app.use(express.json());

dbConnect();

app.use('/nodes', nodeRouter);
app.use('/health', healthRouter);
app.use('/reputation', reputationRouter);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Node Registry running on port ${PORT}`);
}); 