<template>
    <div id="app">
        <!--<img src="./assets/logo.png">-->
        <router-view/>
    </div>
</template>

<script>
    export default {
        name: 'App'
    }
</script>

<style>
    #app {
        font-family:  sans-serif, Arial,  'Avenir', Helvetica;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        margin-top: 0px;
    }

</style>
