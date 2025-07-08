import mongoose from 'mongoose';

export async function dbConnect() {
  try {
    await mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/duxos_registry');
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('MongoDB connection error:', error);
    process.exit(1);
  }
} 