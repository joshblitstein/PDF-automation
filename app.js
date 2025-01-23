const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(cors());

app.post('/process-pdf', multer({ dest: 'uploads/' }).single('source'), async (req, res) => {
    if (!req.file) return res.status(400).json({error: 'PDF required'});

    try {
        await new Promise((resolve, reject) => {
            const python = spawn('./venv/bin/python3', ['pdf_image_test.py']);
            python.on('close', code => code === 0 ? resolve() : reject());
        });

        const pdf = fs.readFileSync('output_with_content.pdf');
        res.json({ success: true, data: pdf.toString('base64') });
    } catch (error) {
        res.status(500).json({error: error.message});
    }
});

app.listen(3000);