import React, {useState} from "react"; // importa o react e o use state, que é um hook usado para armazenar o estado da interface ( por exemplo o texto digitado, e as mensagens anteriores )

import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, SafeAreaView, useWindowDimensions } from 'react-native';

// importa os componentes principais do react native, view que serve como uma div para agrupar elementos, o text que obviamente mostra os textos, o textInput que abre um campo de input, o touchableopacity que gera um botão clicavél, o flatlist que é uma lista com rolagem, e o stylesheet que é onde os estilos css é definido



type Message = {
  id: string;
  text: string;
};

// tipagem do tipo de mensagem que irá ser recebido ou enviado pelo front, garantindo que o id da mensagem é único para cada mensagem, sendo ele um número que é armazenado, e a mensagem (text) é do tipo string, literal



export default function ChatScreen() {

  const {width} = useWindowDimensions();
  const containerWidth = width < 600? width * 0.9 : 1000;

  //função principal do componente que irá gerar a tela do chat em si, e é o que será exportado e usado na navegação como uma página
  const [messages, setMessages] = useState<Message[]>([]);
  // cria o estado Message, que teve sua tipagem criada anteriormente, que será um array de mensagens, o useState é usado para armazenar valores, e os atualizar durante o uso do aplicativo

  // nesse caso o useState que é do tipo Message, retorna um array com dois itens, o valor atual, que seria messages, e o valor atualizado que será o setMessages, que é a string que o usuário irá digitar (**AQUI ELE PE RESPONSAVEL PELAS MENSAGENS EXISTENTES (Historico) **)
  const [inputText, setInputText] = useState('');
  // aqui o useState inicia com um valor nulo ' ', sendo ele o inputText, mas enquanto o usuário digita, ele é atualizado pelo setInputText (**AQUI É O ARMAZENAMENTO NO CAMPO DE INPUT**)






  const handleSend = () => {
    // criamos a const handlesend e usamos => como atribuição, que é conhecida como atribuição arrow em react
    if (inputText.trim()) {
      //inputText é o que o usuário digitar, definido no const acima, o .trim é responsável por tirar os espaçamentos em branco no inicio e no fim da string
      // o if esta verificando se o usuário digitou algo, ou seja, não deixou o campo de input em branco

      setMessages([...messages, { id: Date.now().toString(), text: inputText }]);
      // setMessages é a parte atualizada do histórico de mensagens que definimos na const dentro da função ChatScreen, ao chamar ela, o react redesenha a tela com as novas mensagens, mantendo o histórico
      // ao passar de parametro para SetMessages, os parametros ...messages ( isso significa que estamos pegando todas, todas as mensagens anteriores, o id e o text criam uma nova mensagem) o date.now retorna a hora exata em milissegundos, e o toString converte para string, assim sendo, toda mensagem tem id unico, pois nenhuma mensagem é enviada no mesmo milissegundo
      // ou seja, esse campo estamos fazendo que seja o seguinte, o setMessages vai pegar todas as mensagens anteriores, e vai adicionar essa nova que estamos colocando no input na frente de todas, salvando em forma de lista de palavras

      setInputText('');
      // isso limpa o campo do usuário após ele ter enviado alguma mensagem 
    }
  };

  return (
    //irá retornar o que vai ser exibido na tela
    <SafeAreaView style={styles.safeArea}>
    <View style={[styles.container, { width : containerWidth}]}>
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.messageBubble}>
            <Text style={styles.messageText}>{item.text}</Text>
          </View>
        )}
        contentContainerStyle={styles.chatContainer}
      />

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Digite sua mensagem..."
          value={inputText}
          onChangeText={setInputText}
        />
        <TouchableOpacity onPress={handleSend} style={styles.sendButton}>
          <Text style={styles.sendButtonText}>Enviar</Text>
        </TouchableOpacity>
      </View>
    </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#4B3D3D',  // atras do container o vinho
  },
  container: {

    flex: 1,
    backgroundColor: '#bfb493',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    margin : 20,
    alignSelf : 'center',
  
  },
  chatContainer: {
    padding: 20,
    
    
  },
  messageBubble: {
    backgroundColor: 'white',
    padding: 10,
    borderRadius: 10,
    marginVertical: 5,
    alignSelf: 'flex-start', 
    
  },
  messageText: {
    fontSize: 16,
    padding : 10
    
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 20,
    borderTopWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
    alignItems: 'center',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  input: {
    flex: 1,
    height: 50,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    marginRight: 10,
     borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  sendButton: {
    backgroundColor: '#465575',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

