import click
import requests


@click.group()
def cli():
    """wis2downloader CLI."""
    pass


@click.command('run-dev')
@click.pass_context
def run_dev(ctx):
    """Run the wis2downloader in dev mode"""
    from wis2downloader.app import run
    run()

@click.command('list-subscriptions')
@click.option("--host", type=click.STRING, required=False, default="localhost", help="Host the wis2downloader is running on")
@click.option("--port", type=click.INT, required=False, default=5000, help="Port the wis2downloader is running on")
@click.pass_context
def list_subscriptions(ctx, host, port):
    """list all subscriptions"""

    # make a GET requests to http://{DOWNLOAD_URL}/subscriptions
    DOWNLOAD_URL = f"http://{host}:{port}"
    try:
        response = requests.get(f'{DOWNLOAD_URL}/subscriptions')
        # check response status
        if response.status_code == 200:
            click.echo('Current subscriptions:')
            click.echo(response.text)
        else:
            click.echo(f'Error: {response.status_code}')
            click.echo(response.text)
    except requests.exceptions.ConnectionError:
        click.echo('Error: Connection refused')
        click.echo(f'Is the wis2downloader running on {DOWNLOAD_URL}?')


@click.command('add-subscription')
@click.pass_context
@click.option("--host", type=click.STRING, required=False, default="localhost", help="Host the wis2downloader is running on")
@click.option("--port", type=click.INT, required=False, default=5000, help="Port the wis2downloader is running on")
@click.option('--topic', '-t', help='The topic to subscribe to', required=True)
def add_subscription(ctx, host, port, topic):
    """add a subscription"""

    # make a POST request to http://{DOWNLOAD_URL}/subscriptions
    DOWNLOAD_URL = f"http://{host}:{port}"
    try:
        response = requests.post(f'{DOWNLOAD_URL}/subscriptions',
                                 json={'topic': topic})
        # check response status
        if response.status_code == 201:
            click.echo('Subscription added')
            click.echo('Added subscription:')
            click.echo(response.text)
        else:
            click.echo('Subscription not added')
            click.echo(f'Error: {response.status_code}')
            click.echo(response.text)
    except requests.exceptions.ConnectionError:
        click.echo('Error: Connection refused')
        click.echo(f'Is the wis2downloader running on {DOWNLOAD_URL}?')


@click.command('remove-subscription')
@click.pass_context
@click.option("--host", type=click.STRING, required=False, default="localhost", help="Host the wis2downloader is running on")
@click.option("--port", type=click.INT, required=False, default=5000, help="Port the wis2downloader is running on")
@click.option('--topic', '-t', help='The topic to subscribe to', required=True)
def remove_subscription(ctx, host, port, topic):
    """remove a subscription"""

    topic = topic.replace('#', '%23')
    topic = topic.replace('+', '%2B')
    # make a DELETE request to http://{DOWNLOAD_URL}/subscriptions
    DOWNLOAD_URL = f"http://{host}:{port}"
    try:
        response = requests.delete(
            f'{DOWNLOAD_URL}/subscriptions/{topic}')  # noqa
        # check response status
        if response.status_code == 200:
            click.echo('Subscription deleted')
            click.echo('Current subscriptions:')
            click.echo(response.text)
        else:
            click.echo('Subscription not deleted')
            click.echo(f'Error: {response.status_code}')
            click.echo(response.text)
    except requests.exceptions.ConnectionError:
        click.echo('Error: Connection refused')
        click.echo(f'Is the wis2downloader running on {DOWNLOAD_URL}?')


cli.add_command(run_dev)
cli.add_command(list_subscriptions)
cli.add_command(add_subscription)
cli.add_command(remove_subscription)