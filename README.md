# Poliedro

Projeto Integrador Interdisciplinar dos cursos de Sistemas da Informação, Ciência da Computação, Ciência de Dados e Inteligência Artificial, parceria com o projeto desenvolvido pelo Poliedro.
Instituto Mauá de Tecnologia (IMT) - Primeiro Semestre 2025

Eike --> 24.00682-3 --> @.dev-eike

Gustavo --> 24.00805-2 --> @.Guimaaz

Guilherme Duarte --> 24.00888-5 --> @guimduarte.

Mateusz --> 24.01627-6 --> @Mattcs1206.

passo a passo de como rodar a aplicação

python -m pip install Flask
pip install google-generativeai
pip install python-dotenv
criar .env e colocar a api ( developer )

baixar o expo, npm install expo

caso o sistema implicar com script

Set-ExecutionPolicy -Scope Process -executionPolicy Bypass ( isso deixa os scripts modificaveis uma vez )

após isso

cd chatbot_frontend

npx expo start --tunnel

e para rodar a api

na raiz do projeto - python api.py

ir no arquivo cd chatbot_frontend/utils/api.js e na const api_base_url por seu ip :5000
