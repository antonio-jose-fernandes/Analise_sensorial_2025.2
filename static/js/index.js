const express = require("express");
const cors = require("cors");
const app = express();

const usuarioRoutes = require('./src/routes/usuarioRoutes');

app.use(express.json());
app.use(cors());

app.get('/hello_word', (req, res) => {
  res.send('Testando');
});

app.use("/usuarios", usuarioRoutes);

app.listen(port, () => {
  console.log(`Servidor rodando na porta: http://localhost:${port}`);
});