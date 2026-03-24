terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_deployment" "tegola" {
  metadata {
    name = "tegola-tile-server"
  }
  spec {
    replicas = 2
    selector {
      match_labels = {
        app = "tegola"
      }
    }
    template {
      metadata {
        labels = {
          app = "tegola"
        }
      }
      spec {
        container {
          name              = "tegola"
          image             = "tegola-plastic:latest"
          image_pull_policy = "Never"
          port {
            container_port = 8080
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "tegola" {
  metadata {
    name = "tegola-service"
  }
  spec {
    selector = {
      app = "tegola"
    }
    port {
      port        = 8080
      target_port = 8080
    }
    type = "NodePort"
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "tegola_hpa" {
  metadata {
    name = "tegola-hpa"
  }
  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = "tegola-tile-server"
    }
    min_replicas = 1
    max_replicas = 5
  }
}
