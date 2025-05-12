import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Image, SafeAreaView, useWindowDimensions } from 'react-native';
// safeareaview garente que os itens dos celulares nao sobreponham a interface, por exemplo o dentinho do iphone


export default function App() {
  const [telefone, setTelefone] = useState('');
  const [senha, setSenha] = useState('');
  
  const { width } = useWindowDimensions(); // atualiza o tamanho da tela em tempo real ( ou seja, dependendo do tamanho da tela do celular, estando deitado ou nao, ele pega em tempo real e utiliza no const abaixo)
  const inputWidth = width < 600 ? width * 0.7 : 700;
  const containerWidth = width < 600 ? width * 0.9 : 1000; // o mesmo, mas para o container
  const handleLogin = () => {
    //teste de quando é funcional o alert
    alert('Login clicado!');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={[styles.container, {width : containerWidth }]}>
        <View style={styles.topContainer}>
          <Image
             source={require('../../assets/images/logopoliedro.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>


        <View style={styles.loginContainer}>
          <Text style={styles.title}>Login</Text>

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Número de telefone"
            keyboardType="phone-pad"
            value={telefone}
            onChangeText={setTelefone}
          />

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Senha"
            secureTextEntry
            value={senha}
            onChangeText={setSenha}
          />

          <TouchableOpacity style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>Entrar</Text>
          </TouchableOpacity>
        </View>

        
        <View style={styles.bottomRounded} />
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
    backgroundColor: '#e0e0e0', // fundo principal
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    margin: 20,
    overflow: 'hidden',
    alignSelf: 'center'
    
  },
  topContainer: {
    backgroundColor: '#fff',
    paddingTop: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderColor: '#ccc',
    paddingBottom: 10,
  },
  logo: {
    width: 120,
    height: 50,
  },
  loginContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    marginBottom: 40,
    color: '#000',
    fontFamily : "Cal Sans"

  },
  input: {
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 25,
    paddingHorizontal: 20,
    fontSize: 16,
    marginBottom: 20,
  },
  button: {
    width: 150,
    backgroundColor: '#5C75A7',
    paddingVertical: 12,
    borderRadius: 25,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
  },
  bottomRounded: {
    height: 50,
    backgroundColor: '#5C75A7',
    
  },
});
