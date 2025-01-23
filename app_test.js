const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const multer = require('multer');
const cors = require('cors');
const readline = require('readline');

// Web server setup
const app = express();
app.use(cors());

// Ensure required directories exist
['uploads', 'output'].forEach((dir) => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir);
});

// Function to process a PDF file
function processPDF(filePath) {
  console.log(`Starting to process: ${filePath}`);
  
  // Generate output file name
  const parsedPath = path.parse(filePath);
  const outputFilePath = path.join(parsedPath.dir, `${parsedPath.name}_output${parsedPath.ext}`);

  const python = spawn('./venv/bin/python3', ['pdf_image.py', filePath, outputFilePath]);

  python.stdout.on('data', (data) => {
    console.log('Processing:', data.toString());
  });

  python.stderr.on('data', (data) => {
    console.error('Error:', data.toString());
  });

  python.on('close', (code) => {
    if (code === 0) {
      console.log(`Success! Output saved as: ${outputFilePath}`);
    } else {
      console.log('Processing failed.');
    }
  });
}

// API endpoint for web uploads
app.post('/process-pdf', multer({ dest: 'uploads/' }).single('source'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'PDF required' });

  try {
    console.log(req.file.path);

    const parsedPath = path.parse(req.file.path);
    const outputFilePath = path.join(parsedPath.dir, `${parsedPath.name}_output${parsedPath.ext}`);

    await new Promise((resolve, reject) => {
      const python = spawn('./venv/bin/python3', ['pdf_image.py', req.file.path, outputFilePath]);
      python.on('close', (code) => (code === 0 ? resolve() : reject(new Error('Processing failed'))));
    });

    const pdf = fs.readFileSync(outputFilePath);
    res.json({ success: true, data: pdf.toString('base64'), outputFileName: path.basename(outputFilePath) });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
const server = app.listen(3000, () => {
  console.log('Server running on port 3000');
});

// CLI mode: Listen for file paths dropped into the terminal
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

console.log('Drop a file path into the terminal to process it.');

// Handle file paths dropped into the terminal
rl.on('line', (input) => {
  // Trim and remove any surrounding quotes
  const sanitizedInput = input.trim().replace(/^['"]|['"]$/g, '');

  // Convert to absolute path if necessary
  const absolutePath = path.isAbsolute(sanitizedInput)
    ? sanitizedInput
    : path.resolve(process.cwd(), sanitizedInput);

  console.log(`Received file path: ${absolutePath}`);

  // Check if the file exists
  if (fs.existsSync(absolutePath)) {
    console.log(`Processing file: ${absolutePath}`);
    processPDF(absolutePath);
  } else {
    console.error(`Invalid file path: "${absolutePath}". File does not exist.`);
  }
});
