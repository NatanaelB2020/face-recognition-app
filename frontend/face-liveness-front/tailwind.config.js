/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // --- Cores Baseadas na Imagem (Tema Escuro/Corporativo) ---

        // Fundo Principal do Conteúdo (o branco da área de trabalho)
        'background-light': '#FFFFFF', 
        
        // Fundo da Barra Lateral e Header (o cinza escuro/azulado)
        'gray-dark-sidebar': '#36495B', 

        // Cor de Destaque/Marca (o azul vibrante do logo e botões)
        'primary-brand': '#3498DB', 
        
        // Cor para o Alerta de Erro/Status (o vermelho do 'Funcionário Não Vinculado')
        'status-error': '#E74C3C', 
        'status-error-light': '#FDDEDE', // Fundo claro do alerta de erro
        
        // Cores de texto padrão
        'text-default': '#333333',
        'text-light': '#EEEEEE',
      },
    },
  },
  plugins: [],
}