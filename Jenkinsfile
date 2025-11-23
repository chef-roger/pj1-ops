// Jenkinsfile - Pipeline for the Real-Time Chat App

pipeline {
    agent any

    environment {
        // Docker Hub variables remain here
        IMAGE_NAME = 'chat-app'
        DOCKER_REGISTRY = 'steziwara/chat-app'
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials' 
    }

    stages {
        // Stages 1, 2, and 3 remain correctly executed
        stage('Checkout Code') {
            steps { git branch: 'main', url: 'https://github.com/chef-roger/pj1-ops.git' }
        }

        stage('Build Image') {
            steps {
                script {
                    def customTag = "build-${env.BUILD_NUMBER}"
                    sh "docker build -t ${DOCKER_REGISTRY}:${customTag} ."
                    env.IMAGE_TAG = customTag
                }
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    // Ultra-Safe Docker Login via Stdin
                    sh "echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin docker.io"
                    sh "docker push ${DOCKER_REGISTRY}:${IMAGE_TAG}"
                    sh "docker logout"
                }
            }
        }

        // Stage 4: Secure Deployment Containers
        stage('Deploy Containers') {
            steps {
                // Securely inject DB secrets into the shell environment for Docker Compose
                withCredentials([
                    string(credentialsId: 'db-root-password', variable: 'DB_ROOT_PASSWORD'),
                    string(credentialsId: 'db-user', variable: 'DB_USER')
                    // Note: DB_ROOT_PASSWORD is reused for DATABASE_PASSWORD in the web service,
                    // so we only need to load it once.
                ]) {
                    // Stops and removes the old running containers gracefully
                    sh 'docker compose down'

                    // Starts the new containers. Docker Compose automatically reads
                    // the DB variables (DB_ROOT_PASSWORD, DB_USER) from the shell environment.
                    sh 'docker compose up -d'
                }
            }
        }
    }
}
