# ping-probe

This is a simple script to continuously ping various hosts and export connectivity metrics in Prometheus format.

## How to run

Create a config.yaml file, see config.yaml.example for documentation and an example.

The container can be built and run as follows:

```sh
podman build . --build-arg USER=`id -u` -t $image_tag
podman run --rm -ti -v $PWD/config.yaml:/app/config.yaml:z -p 8000:8000 $image_tag
```

# License

MIT, see [LICENSE](LICESE).